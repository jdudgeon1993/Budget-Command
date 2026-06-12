
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_649c74b44725f0cda32bd0d3efd349a2 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_0aa67dc779c692a1aecd12536af7a26c = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.close_sheet", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["fontSize"] : "20px", ["color"] : "#606088", ["cursor"] : "pointer", ["&:hover"] : ({ ["color"] : "#FFFFFF" }) }),onClick:on_click_0aa67dc779c692a1aecd12536af7a26c},children)
    )
});
