
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_7923821785e6c9c2b96229667353f164 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_83ec22c368cc6228656c63a849b242a3 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_ledger_query", ({ ["q"] : "" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["color"] : "#606088", ["cursor"] : "pointer", ["fontSize"] : "18px", ["&:hover"] : ({ ["color"] : "#FFFFFF" }) }),onClick:on_click_83ec22c368cc6228656c63a849b242a3},children)
    )
});
