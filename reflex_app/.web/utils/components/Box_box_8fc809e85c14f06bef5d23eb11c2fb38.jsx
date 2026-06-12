
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_8fc809e85c14f06bef5d23eb11c2fb38 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_0aa67dc779c692a1aecd12536af7a26c = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.close_sheet", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["fontSize"] : "20px", ["color"] : "#6868a2", ["cursor"] : "pointer", ["&:hover"] : ({ ["color"] : "#f0f0fa" }) }),onClick:on_click_0aa67dc779c692a1aecd12536af7a26c},children)
    )
});
